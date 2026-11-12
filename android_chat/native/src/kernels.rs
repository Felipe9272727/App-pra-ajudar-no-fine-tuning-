#[inline]
pub fn bf16(x: f32) -> f32 {
    let b=x.to_bits();
    if b & 0x7f800000 == 0x7f800000 {return x;}
    f32::from_bits((b.wrapping_add(0x7fff+((b>>16)&1))) & 0xffff0000)
}
#[inline] pub fn read_bf(b:&[u8])->f32 {f32::from_bits((u16::from_le_bytes([b[0],b[1]]) as u32)<<16)}
#[inline] pub fn read_f32(b:&[u8])->f32 {f32::from_le_bytes(b[..4].try_into().unwrap())}
#[inline] pub fn sigmoid(x:f32)->f32 {1./(1.+(-x).exp())}
#[inline] pub fn silu(x:f32)->f32 {x*sigmoid(x)}
pub fn round(v:&mut [f32]) {for x in v {*x=bf16(*x);}}
pub fn rms(x:&[f32],w:&[f32],zero_centered:bool)->Vec<f32> {
    let inv=(x.iter().map(|v|v*v).sum::<f32>()/x.len() as f32+1e-6).sqrt().recip();
    x.iter().zip(w).map(|(x,w)|bf16(x*inv*(if zero_centered {1.+w}else{*w}))).collect()
}
pub fn softmax(x:&[f32])->Vec<f32> {
    let m=x.iter().copied().fold(f32::NEG_INFINITY,f32::max);
    let mut v:Vec<_>=x.iter().map(|x|(x-m).exp()).collect();let sum:f32=v.iter().sum();for x in &mut v {*x/=sum;}v
}
pub fn dot_bf(data:&[u8],x:&[f32])->f32 {
    #[cfg(target_arch="x86_64")] {if std::is_x86_feature_detected!("avx2") {return unsafe{x86_bf(data,x)};}}
    #[cfg(target_arch="aarch64")] {return unsafe{arm_bf(data,x)};}
    #[allow(unreachable_code)] x.iter().enumerate().map(|(i,x)|read_bf(&data[2*i..])*x).sum()
}
pub fn dot_q8(data:&[u8],x:&[f32])->f32 {
    #[cfg(target_arch="x86_64")] {if std::is_x86_feature_detected!("avx2") {return unsafe{x86_q8(data,x)};}}
    #[cfg(target_arch="aarch64")] {return unsafe{arm_q8(data,x)};}
    #[allow(unreachable_code)] {
        let mut s=0.;for (i,c) in x.chunks_exact(32).enumerate(){let b=&data[i*36..];let scale=read_f32(b);for j in 0..32{s+=(b[4+j] as i8 as f32*scale)*c[j];}}s
    }
}
#[cfg(target_arch="x86_64")]
#[target_feature(enable="avx2")]
unsafe fn x86_bf(data:&[u8],x:&[f32])->f32 {
    use std::arch::x86_64::*;let mut acc=_mm256_setzero_ps();let n=x.len()/8*8;
    for i in (0..n).step_by(8){let b=_mm_loadu_si128(data.as_ptr().add(i*2) as *const __m128i);let w=_mm256_castsi256_ps(_mm256_slli_epi32::<16>(_mm256_cvtepu16_epi32(b)));acc=_mm256_add_ps(acc,_mm256_mul_ps(w,_mm256_loadu_ps(x.as_ptr().add(i))));}
    let mut v=[0.;8];_mm256_storeu_ps(v.as_mut_ptr(),acc);let mut s:f32=v.iter().sum();for i in n..x.len(){s+=read_bf(&data[i*2..])*x[i];}s
}
#[cfg(target_arch="x86_64")]
#[target_feature(enable="avx2")]
unsafe fn x86_q8(data:&[u8],x:&[f32])->f32 {
    use std::arch::x86_64::*;let mut acc=_mm256_setzero_ps();
    for i in 0..x.len()/32 {let b=data.as_ptr().add(i*36);let scale=_mm256_set1_ps(read_f32(&data[i*36..]));for j in 0..4 {let q=_mm_loadl_epi64(b.add(4+j*8) as *const __m128i);let w=_mm256_mul_ps(_mm256_cvtepi32_ps(_mm256_cvtepi8_epi32(q)),scale);acc=_mm256_add_ps(acc,_mm256_mul_ps(w,_mm256_loadu_ps(x.as_ptr().add(i*32+j*8))));}}
    let mut v=[0.;8];_mm256_storeu_ps(v.as_mut_ptr(),acc);v.iter().sum()
}
#[cfg(target_arch="aarch64")]
unsafe fn arm_bf(data:&[u8],x:&[f32])->f32 {
    use std::arch::aarch64::*;let mut acc=vdupq_n_f32(0.);let n=x.len()/4*4;
    for i in (0..n).step_by(4){let u=vld1_u16(data.as_ptr().add(i*2) as *const u16);let w=vreinterpretq_f32_u32(vshll_n_u16::<16>(u));acc=vaddq_f32(acc,vmulq_f32(w,vld1q_f32(x.as_ptr().add(i))));}
    let mut s=vaddvq_f32(acc);for i in n..x.len(){s+=read_bf(&data[i*2..])*x[i];}s
}
#[cfg(target_arch="aarch64")]
unsafe fn arm_q8(data:&[u8],x:&[f32])->f32 {
    use std::arch::aarch64::*;let mut acc=vdupq_n_f32(0.);
    for i in 0..x.len()/32 {let b=data.as_ptr().add(i*36);let scale=vdupq_n_f32(read_f32(&data[i*36..]));for j in 0..4 {let q=vmovl_s8(vld1_s8(b.add(4+j*8) as *const i8));let lo=vmulq_f32(vcvtq_f32_s32(vmovl_s16(vget_low_s16(q))),scale);let hi=vmulq_f32(vcvtq_f32_s32(vmovl_s16(vget_high_s16(q))),scale);acc=vaddq_f32(acc,vmulq_f32(lo,vld1q_f32(x.as_ptr().add(i*32+j*8))));acc=vaddq_f32(acc,vmulq_f32(hi,vld1q_f32(x.as_ptr().add(i*32+j*8+4))));}}
    vaddvq_f32(acc)
}
#[cfg(test)]
mod tests {
 use super::*;
 #[test] fn rounding_ties(){assert_eq!(bf16(1.+1./256.),1.);assert_eq!(bf16(1.+3./256.),1.+2./128.);}
 #[test] fn quantized_dot_matches_scalar(){let x:Vec<_>=(0..64).map(|i|i as f32/16.-2.).collect();let mut data=Vec::new();for b in 0..2{data.extend_from_slice(&(0.015f32*(b+1) as f32).to_le_bytes());for j in 0..32{data.push((j as i8-16) as u8);}}let mut expected=0.;for i in 0..64{expected+=((i%32) as f32-16.)*0.015*((i/32+1) as f32)*x[i];}assert!((dot_q8(&data,&x)-expected).abs()<1e-4);}
 #[test] fn bf_dot_matches_float(){let x:Vec<_>=(0..64).map(|i|i as f32/8.).collect();let mut b=Vec::new();for v in &x{b.extend_from_slice(&((bf16(*v).to_bits()>>16) as u16).to_le_bytes());}let reference:f32=x.iter().map(|v|v*v).sum();assert_eq!(dot_bf(&b,&x),reference);}
}

import com.android.apksig.ApkSigner;
import com.android.apksig.util.*;
import com.android.apksig.internal.util.ChainedDataSource;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.security.*;
import java.security.cert.X509Certificate;
import java.util.*;
/** Signs a build intermediate without making another multi-GB copy.
 * Verifies the complete output payload prefix before changing any original byte.
 * Buffers only the small signing block/central-directory tail. */
public final class TailSigner implements ReadableDataSink,AutoCloseable {
 final RandomAccessFile original;final long boundary;long position=0;final ByteArrayOutputStream tail=new ByteArrayOutputStream();
 TailSigner(File file,long boundary)throws Exception{this.original=new RandomAccessFile(file,"r");this.boundary=boundary;}
 public void consume(byte[] b,int off,int len)throws IOException{
  int prefix=(int)Math.min((long)len,Math.max(0,boundary-position));
  if(prefix>0){byte[] check=new byte[Math.min(prefix,65536)];int checked=0;while(checked<prefix){int n=Math.min(check.length,prefix-checked);original.seek(position+checked);original.readFully(check,0,n);for(int i=0;i<n;i++)if(check[i]!=b[off+checked+i])throw new IOException("Signer changed payload prefix at "+(position+checked+i));checked+=n;}}
  if(len>prefix){if(tail.size()+len-prefix>16*1024*1024)throw new IOException("Signing tail too large");tail.write(b,off+prefix,len-prefix);}position+=len;
 }
 public void consume(ByteBuffer b)throws IOException{byte[] chunk=new byte[Math.min(65536,Math.max(1,b.remaining()))];while(b.hasRemaining()){int n=Math.min(chunk.length,b.remaining());b.get(chunk,0,n);consume(chunk,0,n);}}
 private DataSource current(){return new ChainedDataSource(new DataSource[]{DataSources.asDataSource(original,0,Math.min(position,boundary)),DataSources.asDataSource(ByteBuffer.wrap(tail.toByteArray()))});}
 public long size(){return position;}
 public ByteBuffer getByteBuffer(long o,int n)throws IOException{return current().getByteBuffer(o,n);}
 public void feed(long o,long n,DataSink s)throws IOException{current().feed(o,n,s);}
 public void copyTo(long o,int n,ByteBuffer b)throws IOException{current().copyTo(o,n,b);}
 public DataSource slice(long o,long n){return current().slice(o,n);}
 public void close()throws IOException{original.close();}
 public static void main(String[] a)throws Exception{
  File input=new File(a[0]);long boundary=Long.parseLong(a[1]);char[] pass=new String(Files.readAllBytes(Paths.get(a[3])),java.nio.charset.StandardCharsets.UTF_8).trim().toCharArray();
  KeyStore ks=KeyStore.getInstance("PKCS12");try(InputStream in=new FileInputStream(a[2])){ks.load(in,pass);}PrivateKey key=(PrivateKey)ks.getKey("liquid-sense-fast",pass);X509Certificate cert=(X509Certificate)ks.getCertificate("liquid-sense-fast");
  ApkSigner.SignerConfig config=new ApkSigner.SignerConfig.Builder("liquid-sense-fast",key,Collections.singletonList(cert)).build();
  byte[] finalTail;long total;
  try(TailSigner out=new TailSigner(input,boundary)){
   new ApkSigner.Builder(Collections.singletonList(config)).setInputApk(input).setOutputApk(out).setAlignmentPreserved(true).setAlignFileSize(false).setMinSdkVersion(28).setV1SigningEnabled(false).setV2SigningEnabled(false).setV3SigningEnabled(true).setV4SigningEnabled(false).build().sign();
   if(out.position<=boundary||out.tail.size()!=out.position-boundary)throw new IOException("Incomplete signed tail");finalTail=out.tail.toByteArray();total=out.position;
   if(!new String(finalTail,java.nio.charset.StandardCharsets.ISO_8859_1).contains("APK Sig Block 42"))throw new IOException("Signature block missing");
  }
  // All verification of the original prefix completed successfully. Only a
  // rebuildable unsigned intermediate is modified, never a previous release.
  try(RandomAccessFile target=new RandomAccessFile(input,"rw")){target.seek(boundary);target.write(finalTail);target.setLength(total);target.getFD().sync();}
  System.out.println("SIGNED_VERIFIED_PREFIX="+boundary+" TAIL_BYTES="+finalTail.length+" TOTAL="+total);
 }
}

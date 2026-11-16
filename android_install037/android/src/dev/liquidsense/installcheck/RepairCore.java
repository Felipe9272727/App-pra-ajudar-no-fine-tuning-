package dev.liquidsense.installcheck;
import java.io.*;import java.net.*;import java.security.*;import java.util.*;
/** Byte-level recovery of a pinned public ZIP. No Android or model dependency. */
public final class RepairCore {
 public interface Progress {void update(String stage,int done,int total);}
 public interface Fetcher {byte[] get(long start,int length)throws Exception;}
 public static final class Profile {
  public final long size;public final int block;public final String sha;public final String[] hashes;
  public Profile(long size,int block,String sha,String[] hashes){if(size<=0||block<=0||hashes.length!=(size+block-1)/block)throw new IllegalArgumentException("Manifesto inválido");this.size=size;this.block=block;this.sha=sha;this.hashes=hashes;}
  public int length(int index){return (int)Math.min(block,size-(long)index*block);}
 }
 public static final class Scan {public final List<Integer> bad=new ArrayList<>();public String sha;public long bytes;public long missingBytes(Profile p){long n=0;for(int i:bad)n+=p.length(i);return n;}}
 public static String hex(byte[] b){StringBuilder out=new StringBuilder();for(byte v:b)out.append(String.format(Locale.ROOT,"%02x",v&255));return out.toString();}
 public static String digest(byte[] b)throws Exception{return hex(MessageDigest.getInstance("SHA-256").digest(b));}
 public static String digest(File file)throws Exception{MessageDigest h=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){byte[] b=new byte[1048576];int n;while((n=in.read(b))!=-1)h.update(b,0,n);}return hex(h.digest());}
 public static Scan scan(File file,Profile p,Progress progress)throws Exception{
  Scan s=new Scan();s.bytes=file.length();MessageDigest whole=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){
   byte[] b=new byte[p.block];for(int i=0;i<p.hashes.length;i++){int want=p.length(i),n=0,r;while(n<want&&(r=in.read(b,n,want-n))!=-1)n+=r;whole.update(b,0,n);MessageDigest part=MessageDigest.getInstance("SHA-256");part.update(b,0,n);if(n!=want||!hex(part.digest()).equals(p.hashes[i]))s.bad.add(i);progress.update("Conferindo blocos",i+1,p.hashes.length);}
   byte[] tail=new byte[1048576];int n;while((n=in.read(tail))!=-1)whole.update(tail,0,n);
  }s.sha=hex(whole.digest());return s;
 }
 public static void repair(File file,Profile p,Scan scan,Fetcher fetch,Progress progress)throws Exception{
  try(RandomAccessFile out=new RandomAccessFile(file,"rw")){
   int done=0;for(int i:scan.bad){int len=p.length(i);byte[] bytes=fetch.get((long)i*p.block,len);if(bytes.length!=len||!digest(bytes).equals(p.hashes[i]))throw new IOException("Bloco "+i+" recebido com SHA256 diferente. Instalação bloqueada.");out.seek((long)i*p.block);out.write(bytes);out.getFD().sync();byte[] check=new byte[len];out.seek((long)i*p.block);out.readFully(check);if(!digest(check).equals(p.hashes[i]))throw new IOException("Leitura após gravar o bloco "+i+" não confere.");progress.update("Reparando blocos",++done,scan.bad.size());}out.setLength(p.size);out.getFD().sync();
  }if(file.length()!=p.size||!digest(file).equals(p.sha))throw new IOException("SHA256 final não confere. Nenhuma instalação liberada.");
 }
 public static byte[] range(String source,long start,int length,long total)throws Exception{
  URL url=new URL(source);for(int redirect=0;redirect<7;redirect++){
   String host=url.getHost();if(!url.getProtocol().equals("https")||!(host.equals("github.com")||host.equals("release-assets.githubusercontent.com")||host.equals("objects.githubusercontent.com")))throw new IOException("Destino HTTPS inesperado");
   HttpURLConnection c=(HttpURLConnection)url.openConnection();c.setInstanceFollowRedirects(false);c.setConnectTimeout(30000);c.setReadTimeout(60000);c.setRequestProperty("User-Agent","LiquidSense-Integrity/0.2");c.setRequestProperty("Accept-Encoding","identity");c.setRequestProperty("Range","bytes="+start+"-"+(start+length-1));
   try {int code=c.getResponseCode();if(code==301||code==302||code==303||code==307||code==308){String next=c.getHeaderField("Location");if(next==null)throw new IOException("Redirecionamento sem destino");url=new URL(url,next);continue;}
    String expected="bytes "+start+"-"+(start+length-1)+"/"+total;
    if(code!=206||!expected.equals(c.getHeaderField("Content-Range")))throw new IOException("Servidor não respeitou o intervalo solicitado (HTTP "+code+"). Não baixei o arquivo inteiro.");
    byte[] b=new byte[length];try(InputStream in=c.getInputStream()){int n=0,r;while(n<length&&(r=in.read(b,n,length-n))!=-1)n+=r;if(n!=length||in.read()!=-1)throw new IOException("Tamanho inesperado no bloco recebido");}return b;
   }finally{c.disconnect();}
  }throw new IOException("Redirecionamentos demais");
 }
}

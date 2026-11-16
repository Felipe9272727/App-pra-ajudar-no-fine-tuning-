package dev.liquidsense.installcheck;
import java.io.*;import java.nio.file.*;import java.util.*;import java.util.zip.*;
public final class RepairCoreTest {
 static int checks;static void ok(boolean b,String label){if(!b)throw new AssertionError(label);checks++;System.out.println("PASS "+label);}
 static final RepairCore.Progress SILENT=(s,d,t)->{};
 static RepairCore.Profile profile(byte[] bytes,int block)throws Exception {String[] hashes=new String[(bytes.length+block-1)/block];for(int i=0;i<hashes.length;i++)hashes[i]=RepairCore.digest(Arrays.copyOfRange(bytes,i*block,Math.min(bytes.length,(i+1)*block)));return new RepairCore.Profile(bytes.length,block,RepairCore.digest(bytes),hashes);}
 public static void main(String[] args)throws Exception {
  File f=File.createTempFile("liquid-repair-",".zip");byte[] original=new byte[40001];for(int i=0;i<original.length;i++)original[i]=(byte)(i*17+i/71);RepairCore.Profile p=profile(original,8192);
  try{
   Files.write(f.toPath(),original);RepairCore.Scan scan=RepairCore.scan(f,p,SILENT);ok(scan.bad.isEmpty()&&scan.sha.equals(p.sha),"pristine content");
   byte[] broken=original.clone();broken[9000]^=1;Files.write(f.toPath(),broken);scan=RepairCore.scan(f,p,SILENT);ok(scan.bad.equals(Arrays.asList(1))&&scan.missingBytes(p)==8192,"one changed byte locates exactly one block");
   final int[] transferred={0};RepairCore.repair(f,p,scan,(start,length)->{transferred[0]+=length;return Arrays.copyOfRange(original,(int)start,(int)start+length);},SILENT);ok(Arrays.equals(Files.readAllBytes(f.toPath()),original)&&transferred[0]==8192,"repair downloads only bad block");
   Files.write(f.toPath(),broken);scan=RepairCore.scan(f,p,SILENT);boolean rejected=false;try{RepairCore.repair(f,p,scan,(s,n)->new byte[n],SILENT);}catch(IOException e){rejected=true;}ok(rejected&&Arrays.equals(Files.readAllBytes(f.toPath()),broken),"poisoned network bytes rejected before write");
   rejected=false;try{RepairCore.repair(f,p,scan,(s,n)->new byte[n-1],SILENT);}catch(IOException e){rejected=true;}ok(rejected,"truncated response rejected");
   Files.write(f.toPath(),Arrays.copyOf(original,9001));scan=RepairCore.scan(f,p,SILENT);ok(scan.bad.equals(Arrays.asList(1,2,3,4)),"truncation locates missing blocks");RepairCore.repair(f,p,scan,(s,n)->Arrays.copyOfRange(original,(int)s,(int)s+n),SILENT);ok(RepairCore.digest(f).equals(p.sha),"truncated file recovered");
   Files.write(f.toPath(),Arrays.copyOf(original,original.length+10));scan=RepairCore.scan(f,p,SILENT);ok(scan.bad.isEmpty()&&!scan.sha.equals(p.sha),"extra trailing bytes detectable");RepairCore.repair(f,p,scan,(s,n)->{throw new AssertionError("unneeded fetch");},SILENT);ok(RepairCore.digest(f).equals(p.sha)&&f.length()==p.size,"excess bytes removed only in cache without downloads");
   rejected=false;try{RepairCore.range("http://github.com/file",0,1,1);}catch(IOException e){rejected=true;}ok(rejected,"HTTP rejected");rejected=false;try{RepairCore.range("https://example.com/file",0,1,1);}catch(IOException e){rejected=true;}ok(rejected,"unexpected remote host rejected");
  }finally{f.delete();}
  if(args.length>0){int entries=0;try(ZipInputStream in=new ZipInputStream(new FileInputStream(args[0]))){ZipEntry e;byte[] b=new byte[1048576];while((e=in.getNextEntry())!=null){java.security.MessageDigest sha=java.security.MessageDigest.getInstance("SHA-256");int n;while((n=in.read(b))!=-1)sha.update(b,0,n);if(e.getName().endsWith(".apk"))ok(RepairCore.hex(sha.digest()).equals("4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10"),"full ZIP Java streaming CRC and APK SHA");entries++;}}ok(entries==2,"exact two public ZIP entries");}
  System.out.println("TOTAL_PASS "+checks);
 }
}

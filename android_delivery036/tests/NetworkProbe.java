package dev.liquidsense.installcheck;
public final class NetworkProbe {public static void main(String[] a)throws Exception{byte[] b=RepairCore.range(a[0],Long.parseLong(a[1]),Integer.parseInt(a[2]),Long.parseLong(a[3]));if(!RepairCore.digest(b).equals(a[4]))throw new AssertionError("range bytes do not match pinned block");System.out.println("HTTPS_RANGE_8MiB_PINNED_SHA_PASSED");}}

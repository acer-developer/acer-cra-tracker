import { NextResponse } from "next/server";
import { prisma } from "@/app/lib/db";

export const dynamic = "force-dynamic";

// TEMPORARY diagnostic: reports whether the DB is reachable and, if not, the
// exact error. Remove once the connection is confirmed working.
export async function GET() {
  const hasUrl = Boolean(process.env.DATABASE_URL);
  const hasDirect = Boolean(process.env.DIRECT_URL);
  // Show only the host of DATABASE_URL (never the password) to confirm which
  // string the deployment actually has.
  let host = "unset";
  try {
    host = process.env.DATABASE_URL ? new URL(process.env.DATABASE_URL).host : "unset";
  } catch {
    host = "unparseable";
  }
  try {
    await prisma.$queryRaw`SELECT 1`;
    return NextResponse.json({ ok: true, hasUrl, hasDirect, host });
  } catch (e: any) {
    return NextResponse.json({
      ok: false,
      hasUrl,
      hasDirect,
      host,
      error: String(e?.message ?? e).slice(0, 500),
    });
  }
}

import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/db";
import { Prisma } from "@prisma/client";

export const dynamic = "force-dynamic";

// Mirrors reference /rating-actions/page: newest first, offset paginated,
// optional agency / action / search filters. Undated rows sort last.
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const limit = Math.min(Number(sp.get("limit") ?? 50), 200);
  const offset = Math.max(Number(sp.get("offset") ?? 0), 0);
  const agency = sp.get("agency") || undefined;
  const action = sp.get("action") || undefined;
  const q = sp.get("q") || undefined;

  const where: Prisma.RatingActionWhereInput = {};
  if (agency) where.agency = agency as any;
  if (action) where.ratingAction = action;
  if (q) where.entityName = { contains: q, mode: "insensitive" };

  const [results, total] = await Promise.all([
    prisma.ratingAction.findMany({
      where,
      orderBy: [{ ratingDate: { sort: "desc", nulls: "last" } }, { ingestedAt: "desc" }],
      skip: offset,
      take: limit,
    }),
    prisma.ratingAction.count({ where }),
  ]);

  return NextResponse.json({
    results: results.map((r) => ({
      rating_id: r.id,
      entity_id: r.entityId,
      entity_name: r.entityName,
      agency: r.agency,
      rating_date: r.ratingDate ? r.ratingDate.toISOString().slice(0, 10) : null,
      rating_action: r.ratingAction,
      is_inc: r.isInc,
      superseded: r.superseded,
      top_rating_string: r.topRatingString,
      top_grade: r.topGrade,
      band: r.band,
      top_amount_cr: r.topAmountCr,
      source_url_primary: r.sourceUrlPrimary,
      source_url_display: r.sourceUrlDisplay,
    })),
    total,
  });
}

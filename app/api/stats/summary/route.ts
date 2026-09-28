import { NextResponse } from "next/server";
import { prisma } from "@/app/lib/db";

export const dynamic = "force-dynamic";

// Mirrors the reference /stats/summary shape: totals + breakdowns.
export async function GET() {
  const [total, entities, incCount, byAgency, byAction, byGrade] = await Promise.all([
    prisma.ratingAction.count(),
    prisma.entity.count(),
    prisma.ratingAction.count({ where: { isInc: true } }),
    prisma.ratingAction.groupBy({ by: ["agency"], _count: { _all: true } }),
    prisma.ratingAction.groupBy({ by: ["ratingAction"], _count: { _all: true } }),
    prisma.ratingAction.groupBy({
      by: ["topGrade", "band"],
      _count: { _all: true },
      _sum: { topAmountCr: true },
    }),
  ]);

  return NextResponse.json({
    total_rating_actions: total,
    total_entities: entities,
    inc_count: incCount,
    by_agency: byAgency
      .map((r) => ({ agency: r.agency, count: r._count._all }))
      .sort((a, b) => b.count - a.count),
    by_action: byAction
      .map((r) => ({ action: r.ratingAction, count: r._count._all }))
      .sort((a, b) => b.count - a.count),
    by_grade: byGrade
      .filter((r) => r.topGrade)
      .map((r) => ({
        grade: r.topGrade,
        band: r.band,
        count: r._count._all,
        amount_cr: r._sum.topAmountCr ?? 0,
      }))
      .sort((a, b) => b.count - a.count),
  });
}

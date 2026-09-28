import { prisma } from "@/app/lib/db";

export const dynamic = "force-dynamic";

const fmt = (n: number) => n.toLocaleString("en-IN");

export default async function Overview() {
  // Read straight from the DB in this server component (no self-fetch needed).
  const [total, entities, incCount, byAgency, latest] = await Promise.all([
    prisma.ratingAction.count(),
    prisma.entity.count(),
    prisma.ratingAction.count({ where: { isInc: true } }),
    prisma.ratingAction.groupBy({ by: ["agency"], _count: { _all: true } }),
    prisma.ratingAction.findMany({
      orderBy: [{ ratingDate: { sort: "desc", nulls: "last" } }],
      take: 15,
    }),
  ]);

  const agencies = byAgency
    .map((r) => ({ agency: r.agency, count: r._count._all }))
    .sort((a, b) => b.count - a.count);
  const maxAgency = agencies[0]?.count ?? 1;
  const incPct = total ? Math.round((incCount / total) * 100) : 0;

  return (
    <main className="wrap">
      <h1>ACER CRA Tracker</h1>
      <p className="sub">
        Rating actions parsed from the seven Indian credit rating agencies&rsquo; published
        press releases. Counts reflect what has been ingested.
      </p>

      {total === 0 ? (
        <div className="empty">
          No data yet. Run the ingestion pipeline (see <code>scraper/README.md</code>) to
          populate the database, then refresh.
        </div>
      ) : (
        <>
          <div className="cards">
            <div className="card">
              <div className="label">Rating actions</div>
              <div className="num">{fmt(total)}</div>
              <div className="note">Parsed across seven agencies.</div>
            </div>
            <div className="card">
              <div className="label">Rated borrowers</div>
              <div className="num">{fmt(entities)}</div>
              <div className="note">Distinct entities.</div>
            </div>
            <div className="card">
              <div className="label">Issuer not cooperating</div>
              <div className="num">{fmt(incCount)}</div>
              <div className="note">{incPct}% of actions &mdash; treat as materially stale.</div>
            </div>
            <div className="card">
              <div className="label">Agencies</div>
              <div className="num">{agencies.length}</div>
              <div className="note">CRISIL, CARE, ICRA, India Ratings, Infomerics, Acuit&eacute;, Brickwork.</div>
            </div>
          </div>

          <div className="section">
            <h2>Coverage by agency</h2>
            {agencies.map((a) => (
              <div className="bar-row" key={a.agency}>
                <div>{a.agency}</div>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(a.count / maxAgency) * 100}%` }} />
                </div>
                <div className="num-cell">{fmt(a.count)}</div>
              </div>
            ))}
          </div>

          <div className="section">
            <h2>Latest rating actions</h2>
            <table>
              <thead>
                <tr>
                  <th>Entity</th>
                  <th>Agency</th>
                  <th>Date</th>
                  <th>Action</th>
                  <th>Rating</th>
                  <th>Amount (Cr)</th>
                </tr>
              </thead>
              <tbody>
                {latest.map((r) => (
                  <tr key={r.id}>
                    <td>{r.entityName}</td>
                    <td>{r.agency}</td>
                    <td>{r.ratingDate ? r.ratingDate.toISOString().slice(0, 10) : "—"}</td>
                    <td>{r.ratingAction}</td>
                    <td>
                      <span className={`pill ${r.band}`}>{r.topRatingString ?? r.topGrade ?? "—"}</span>
                    </td>
                    <td className="num-cell">{r.topAmountCr != null ? fmt(r.topAmountCr) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}

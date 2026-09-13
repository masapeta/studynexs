import type { TableBlock } from "@/lib/workspace-types";

export function TableWidget(block: TableBlock) {
  return (
    <section className="sn-workspace sn-workspace--primary p-5 rounded-xl border border-line" style={{ overflowX: "auto" }}>
      <div className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
        {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
        {block.payload.rows.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: 14 }}>{block.payload.empty_message}</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 520 }}>
            <thead>
              <tr>
                {block.payload.columns.map((column) => (
                  <th
                    key={column.key}
                    style={{
                      borderBottom: "1px solid var(--border)",
                      color: "var(--text-muted)",
                      fontSize: 12,
                      fontWeight: 600,
                      padding: "0 0 10px",
                      textAlign: "left",
                    }}
                  >
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.payload.rows.map((row, index) => (
                <tr key={index}>
                  {block.payload.columns.map((column) => (
                    <td
                      key={column.key}
                      style={{
                        borderBottom: "1px solid color-mix(in srgb, var(--border) 70%, transparent)",
                        padding: "12px 0",
                        verticalAlign: "top",
                      }}
                    >
                      {row[column.key] === null ? "-" : String(row[column.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

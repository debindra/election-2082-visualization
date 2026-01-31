import React, { useEffect, useState } from 'react';
import { getSchema, getElectionColumns } from '../services/api';

const ELECTION_YEAR = 2082;

const DataColumnsReview = () => {
  const [schema, setSchema] = useState(null);
  const [columns, setColumns] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getSchema().then(setSchema).catch((e) => setError(e?.message || 'Failed to load schema'));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getElectionColumns(ELECTION_YEAR)
      .then(setColumns)
      .catch((e) => {
        setColumns(null);
        setError(e?.response?.data?.detail || e?.message || 'Failed to load columns');
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="h-full overflow-y-auto bg-white rounded-xl border border-[#1e3a5f]/15 p-4 lg:p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[#1e3a5f] mb-1">Data columns & schema</h2>
        <p className="text-sm text-[#1e3a5f]/70">
          Review supported columns (including English) and first-row sample for the selected election.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-[#b91c1c]/10 border border-[#b91c1c]/30 text-[#b91c1c] text-sm px-4 py-3">
          {error}
        </div>
      )}

      {/* Supported schema: required, optional, English */}
      {schema && (
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-[#1e3a5f]">Supported columns (for review)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg border border-[#1e3a5f]/15 bg-[#1e3a5f]/5 p-4">
              <div className="text-xs font-semibold uppercase tracking-wide text-[#1e3a5f]/70 mb-2">Required</div>
              <ul className="text-sm text-[#1e3a5f] space-y-1">
                {schema.required?.map((c) => (
                  <li key={c.name} className="font-mono">{c.name}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-[#1e3a5f]/15 bg-[#1e3a5f]/5 p-4">
              <div className="text-xs font-semibold uppercase tracking-wide text-[#1e3a5f]/70 mb-2">Optional</div>
              <ul className="text-sm text-[#1e3a5f] space-y-1">
                {schema.optional?.slice(0, 10).map((c) => (
                  <li key={c.name} className="font-mono">{c.name}</li>
                ))}
                {schema.optional?.length > 10 && (
                  <li className="text-[#1e3a5f]/60 font-mono">+{schema.optional.length - 10} more</li>
                )}
              </ul>
            </div>
            <div className="rounded-lg border border-[#1e3a5f]/20 bg-[#1e3a5f]/5 p-4">
              <div className="text-xs font-semibold uppercase tracking-wide text-[#1e3a5f] mb-2">English (for search & display)</div>
              <ul className="text-sm text-[#1e3a5f] space-y-1.5">
                {schema.english?.map((c) => (
                  <li key={c.name} className="border-b border-[#1e3a5f]/15 pb-1.5 last:border-0 last:pb-0">
                    <span className="font-mono font-medium text-[#1e3a5f]">{c.name}</span>
                    <span className="text-[#1e3a5f]/60 block text-xs mt-0.5">{c.description}</span>
                    {c.csv_examples?.length ? (
                      <span className="text-xs text-[#1e3a5f]/50 block mt-0.5">CSV e.g. {c.csv_examples.join(', ')}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Columns + first row for selected year */}
      {loading && <p className="text-sm text-[#1e3a5f]/70">Loading columns…</p>}
      {!loading && columns && (
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-[#1e3a5f]">
            Election {columns.year} — columns & first row
            {columns.english_columns_present?.length ? (
              <span className="ml-2 text-xs font-normal text-[#1e3a5f]/70">
                ({columns.english_columns_present.length} English columns present)
              </span>
            ) : null}
          </h3>
          <div className="rounded-lg border border-[#1e3a5f]/15 overflow-hidden">
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#1e3a5f]/10 border-b border-[#1e3a5f]/20">
                    <th className="text-left py-2 px-3 font-medium text-[#1e3a5f]">Column</th>
                    <th className="text-left py-2 px-3 font-medium text-[#1e3a5f]">Sample (first row)</th>
                  </tr>
                </thead>
                <tbody>
                  {columns.columns?.map((col) => (
                    <tr
                      key={col.name}
                      className={`border-b border-[#1e3a5f]/10 ${col.english ? 'bg-[#1e3a5f]/5' : ''}`}
                    >
                      <td className="py-2 px-3 font-mono text-[#1e3a5f]">
                        {col.name}
                        {col.english && (
                          <span className="ml-2 text-xs text-[#1e3a5f]/70 font-normal">(English)</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-[#1e3a5f]/80 break-all max-w-md">
                        {col.sample != null ? String(col.sample) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataColumnsReview;

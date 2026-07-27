import type { Citation } from "../../types";

const DOC_TYPE_COLORS: Record<string, string> = {
  sop: "bg-green-100 text-green-700 border-green-200",
  manual: "bg-blue-100 text-blue-700 border-blue-200",
  spec: "bg-purple-100 text-purple-700 border-purple-200",
  troubleshooting: "bg-orange-100 text-orange-700 border-orange-200",
  fmea: "bg-red-100 text-red-700 border-red-200",
  case_study: "bg-yellow-100 text-yellow-700 border-yellow-200",
};

function RelevanceDots({ score }: { score: number }) {
  const filled = Math.round(score * 5);
  return (
    <div className="flex gap-0.5" title={`Relevance: ${Math.round(score * 100)}%`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`w-1.5 h-1.5 rounded-full ${i < filled ? "bg-primeev-500" : "bg-gray-200"}`}
        />
      ))}
    </div>
  );
}

function CitationCard({ citation }: { citation: Citation }) {
  const colorClass = DOC_TYPE_COLORS[citation.doc_type] ?? "bg-gray-100 text-gray-700 border-gray-200";
  const docUrl = `/api/docs/${citation.path}`;

  return (
    <a
      href={docUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-lg border border-gray-200 bg-white p-3 hover:border-primeev-400 hover:shadow-sm transition-all group"
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colorClass}`}>
          {citation.doc_type_label}
        </span>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <RelevanceDots score={citation.relevance} />
          <svg
            className="w-3.5 h-3.5 text-gray-400 group-hover:text-primeev-500 transition-colors flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </div>
      </div>

      <div className="text-sm font-medium text-gray-800 leading-snug mb-1 group-hover:text-primeev-700 transition-colors">
        {citation.title}
      </div>

      {citation.station_id && (
        <div className="text-xs text-gray-400 mb-1.5 font-mono">{citation.station_id}</div>
      )}

      {citation.excerpt && (
        <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{citation.excerpt}</p>
      )}
    </a>
  );
}

interface CitationPanelProps {
  citations: Citation[];
  isOpen: boolean;
  onClose: () => void;
}

export default function CitationPanel({ citations, isOpen, onClose }: CitationPanelProps) {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-20"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Slide-over panel */}
      <div
        className={`fixed top-0 right-0 h-full w-80 bg-gray-50 border-l border-gray-200 shadow-xl z-30 flex flex-col transition-transform duration-200 ease-in-out ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
          <div>
            <h3 className="text-sm font-semibold text-gray-800">Sources</h3>
            <p className="text-xs text-gray-400">{citations.length} document{citations.length !== 1 ? "s" : ""} referenced</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close sources panel"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Citation list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {citations.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-400">No sources available</div>
          ) : (
            citations.map((cit) => (
              <CitationCard key={cit.id} citation={cit} />
            ))
          )}
        </div>

        {/* Footer note */}
        <div className="px-4 py-2.5 bg-white border-t border-gray-200">
          <p className="text-xs text-gray-400">Click any source to open the full document</p>
        </div>
      </div>
    </>
  );
}

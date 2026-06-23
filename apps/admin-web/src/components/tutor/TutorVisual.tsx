"use client";

type Props = { kind: string; caption?: string };

export default function TutorVisual({ kind, caption }: Props) {
  return (
    <div className="tutor-visual-wrap">
      {kind === "fraction_bars" && <FractionBars />}
      {kind === "number_line" && <NumberLine />}
      {kind === "photosynthesis" && <PhotosynthesisDiagram />}
      {kind === "triangle" && <TriangleAngles />}
      {kind === "equation" && <EquationBalance />}
      {(kind === "generic" || !["fraction_bars", "number_line", "photosynthesis", "triangle", "equation"].includes(kind)) && (
        <GenericBoard />
      )}
      {caption && <p className="tutor-visual-caption">{caption}</p>}
    </div>
  );
}

function FractionBars() {
  return (
    <svg viewBox="0 0 320 140" className="tutor-svg" role="img" aria-label="Fraction bars diagram">
      <rect x="10" y="20" width="280" height="36" fill="#e2e8f0" rx="6" />
      <rect x="10" y="20" width="140" height="36" fill="#ee6c4d" rx="6" />
      <text x="160" y="44" textAnchor="middle" fontSize="13" fill="#334155" fontWeight="600">1/2</text>
      <rect x="10" y="72" width="280" height="36" fill="#e2e8f0" rx="6" />
      <rect x="10" y="72" width="93" height="36" fill="#3b82f6" rx="6" />
      <text x="160" y="96" textAnchor="middle" fontSize="13" fill="#334155" fontWeight="600">1/3</text>
      <text x="160" y="128" textAnchor="middle" fontSize="12" fill="#64748b">→ make equal parts (LCM)</text>
    </svg>
  );
}

function NumberLine() {
  return (
    <svg viewBox="0 0 320 100" className="tutor-svg" role="img" aria-label="Number line">
      <line x1="20" y1="50" x2="300" y2="50" stroke="#334155" strokeWidth="2" />
      {[0, 1, 2, 3, 4, 5, 6].map((n) => (
        <g key={n}>
          <line x1={20 + n * 40} y1="44" x2={20 + n * 40} y2="56" stroke="#334155" />
          <text x={20 + n * 40} y="72" textAnchor="middle" fontSize="11" fill="#64748b">{n}</text>
        </g>
      ))}
      <circle cx="80" cy="50" r="6" fill="#ee6c4d" />
      <circle cx="140" cy="50" r="6" fill="#3b82f6" />
      <circle cx="180" cy="50" r="8" fill="#0f9d6e" />
      <text x="180" y="30" textAnchor="middle" fontSize="12" fill="#0f9d6e" fontWeight="700">5/6</text>
    </svg>
  );
}

function PhotosynthesisDiagram() {
  return (
    <svg viewBox="0 0 320 180" className="tutor-svg" role="img" aria-label="Photosynthesis diagram">
      <rect x="120" y="60" width="80" height="100" fill="#86efac" rx="8" />
      <ellipse cx="160" cy="50" rx="50" ry="18" fill="#fde68a" />
      <text x="160" y="54" textAnchor="middle" fontSize="11" fill="#b45309">Sunlight</text>
      <text x="50" y="100" fontSize="11" fill="#3b82f6">H₂O</text>
      <path d="M70 95 L115 95" stroke="#3b82f6" markerEnd="url(#arr)" />
      <text x="250" y="90" fontSize="11" fill="#64748b">CO₂</text>
      <path d="M230 85 L205 95" stroke="#64748b" />
      <text x="160" y="130" textAnchor="middle" fontSize="11" fill="#166534" fontWeight="600">Glucose</text>
      <text x="230" y="130" fontSize="11" fill="#0ea5e9">O₂</text>
      <path d="M200 120 L250 125" stroke="#0ea5e9" />
      <defs>
        <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#3b82f6" />
        </marker>
      </defs>
    </svg>
  );
}

function TriangleAngles() {
  return (
    <svg viewBox="0 0 280 160" className="tutor-svg" role="img" aria-label="Triangle angles">
      <polygon points="40,130 240,130 140,30" fill="#eef2ff" stroke="#334155" strokeWidth="2" />
      <text x="55" y="125" fontSize="13" fill="#ee6c4d" fontWeight="700">50°</text>
      <text x="210" y="125" fontSize="13" fill="#3b82f6" fontWeight="700">60°</text>
      <text x="135" y="55" fontSize="13" fill="#0f9d6e" fontWeight="700">70°</text>
      <text x="140" y="155" textAnchor="middle" fontSize="12" fill="#64748b">50 + 60 + 70 = 180°</text>
    </svg>
  );
}

function EquationBalance() {
  return (
    <svg viewBox="0 0 300 120" className="tutor-svg" role="img" aria-label="Equation balance">
      <line x1="150" y1="20" x2="150" y2="90" stroke="#334155" strokeWidth="3" />
      <line x1="80" y1="40" x2="220" y2="40" stroke="#334155" strokeWidth="4" />
      <rect x="60" y="50" width="70" height="36" fill="#fef3c7" rx="6" />
      <text x="95" y="73" textAnchor="middle" fontSize="14" fontWeight="700">2x+4</text>
      <rect x="170" y="50" width="70" height="36" fill="#dbeafe" rx="6" />
      <text x="205" y="73" textAnchor="middle" fontSize="14" fontWeight="700">10</text>
      <text x="150" y="110" textAnchor="middle" fontSize="12" fill="#64748b">same on both sides</text>
    </svg>
  );
}

function GenericBoard() {
  return (
    <svg viewBox="0 0 320 140" className="tutor-svg" role="img" aria-label="Lesson board">
      <rect x="10" y="10" width="300" height="120" fill="#1e293b" rx="12" />
      <text x="30" y="45" fontSize="14" fill="#f8fafc" fontFamily="Georgia, serif">• Key idea</text>
      <text x="30" y="72" fontSize="13" fill="#cbd5e1">• Step by step</text>
      <text x="30" y="99" fontSize="13" fill="#cbd5e1">• Picture + words</text>
      <circle cx="260" cy="70" r="28" fill="none" stroke="#ee6c4d" strokeWidth="3" strokeDasharray="6 4" />
    </svg>
  );
}

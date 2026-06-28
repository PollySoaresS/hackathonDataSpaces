import React from "react";

const ROUTES = [
  { id: 0, name: "El Carmen", detail: "3 paradas · 12 km" },
  { id: 1, name: "Ruzafa", detail: "2 paradas · 8 km" },
  { id: 2, name: "Centro histórico", detail: "1 parada · 5 km" },
  { id: 3, name: "Benimaclet", detail: "1 parada · 7 km" },
];

export default function RouteList({ activeRoute, onSelect, optimized }) {
  return (
    <div className="route-list">
      {ROUTES.map((route, index) => (
        <button
          key={route.id}
          className={`route-item ${index === activeRoute ? "route-item--active" : ""}`}
          onClick={() => onSelect(index)}
        >
          <div>
            <div className="route-name">{route.name}</div>
            <div className="route-detail">{route.detail}</div>
          </div>
          <span className="route-badge">{optimized ? "✓" : "•"}</span>
        </button>
      ))}
    </div>
  );
}

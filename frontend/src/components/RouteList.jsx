import React from "react";
import { Box, ButtonBase, Chip, LinearProgress, Stack, Typography } from "@mui/material";

const ROUTES = [
  { id: 0, code: "A", name: "El Carmen", detail: "3 paradas · 12 km", color: "#ff5050", accent: "#5a1313", on: "#ffffff", mode: "calor alto", load: 92 },
  { id: 1, code: "B", name: "Ruzafa", detail: "2 paradas · 8 km", color: "#8ebdce", accent: "#356373", on: "#000000", mode: "zona sensible", load: 66 },
  { id: 2, code: "C", name: "Centro histórico", detail: "1 parada · 5 km", color: "#c2c2c2", accent: "#3d3d3d", on: "#000000", mode: "cero emisión", load: 48 },
  { id: 3, code: "D", name: "Benimaclet", detail: "1 parada · 7 km", color: "#024ad8", accent: "#0e3191", on: "#ffffff", mode: "eco directa", load: 58 },
];

export default function RouteList({ activeRoute, onSelect, optimized }) {
  return (
    <div className="route-list">
      {ROUTES.map((route, index) => (
        <ButtonBase
          key={route.id}
          className={`route-item ${index === activeRoute ? "route-item--active" : ""}`}
          onClick={() => onSelect(index)}
          sx={{ "--route-color": route.color, "--route-accent": route.accent, "--route-on": route.on }}
        >
          <Box className="route-code">{route.code}</Box>
          <Stack className="route-copy" spacing={0.5}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" gap={1}>
              <Typography className="route-name">{route.name}</Typography>
              <Chip
                size="small"
                label={optimized ? "consolidada" : route.mode}
                className="route-chip"
              />
            </Stack>
            <Typography className="route-detail">{route.detail}</Typography>
            <LinearProgress
              variant="determinate"
              value={optimized ? Math.max(route.load - 26, 24) : route.load}
              className="route-progress"
            />
          </Stack>
        </ButtonBase>
      ))}
    </div>
  );
}

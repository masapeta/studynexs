/** Shared ambient background for authenticated app shells. */
export function AppBackground() {
  return (
    <div className="sn-app-bg" aria-hidden>
      <div className="sn-app-mesh" />
      <div className="sn-app-orb sn-app-orb--1" />
      <div className="sn-app-orb sn-app-orb--2" />
    </div>
  );
}

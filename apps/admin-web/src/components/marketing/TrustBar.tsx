"use client";

import { FadeIn } from "./Motion";
import { Lock, Server, Shield, Users } from "lucide-react";

const TRUST_ITEMS = [
  { icon: Shield, label: "Human-in-the-loop AI" },
  { icon: Lock, label: "India DPDP aligned" },
  { icon: Server, label: "Tenant-isolated data" },
  { icon: Users, label: "Enterprise RBAC" },
];

export function TrustBar() {
  return (
    <section className="mkt-trust" aria-label="Trust and security">
      <div className="mkt-container">
        <FadeIn>
          <div className="mkt-trust-inner mkt-glass">
            {TRUST_ITEMS.map((item) => (
              <div key={item.label} className="mkt-trust-item">
                <item.icon size={16} strokeWidth={2} aria-hidden />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

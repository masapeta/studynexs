import { FinanceHubNav } from "@/components/layout/FinanceHubNav";

export default function FinanceLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <FinanceHubNav />
      {children}
    </>
  );
}

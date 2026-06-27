import { TeachingHubNav } from "@/components/layout/TeachingHubNav";

export default function TeachingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <TeachingHubNav />
      {children}
    </>
  );
}

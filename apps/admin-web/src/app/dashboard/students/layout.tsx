import { StudentsHubNav } from "@/components/layout/StudentsHubNav";

export default function StudentsLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentsHubNav />
      {children}
    </>
  );
}

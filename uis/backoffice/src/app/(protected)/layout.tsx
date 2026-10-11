import { NavMenu } from "@/components/NavMenu";

export default function ProtectedLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <header className="topbar">
        <span className="brand">Nexova · Backoffice</span>
        <NavMenu />
      </header>
      {children}
    </>
  );
}

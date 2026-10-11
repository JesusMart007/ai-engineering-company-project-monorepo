import { AuthGuard } from "@/components/AuthGuard";
import { NavMenu } from "@/components/NavMenu";

// Every page in this group needs a session. The check runs in the browser
// (the token is in localStorage), so there is no middleware involved.
export default function ProtectedLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <AuthGuard>
      <header className="topbar">
        <span className="brand">Nexova · Backoffice</span>
        <NavMenu />
      </header>
      {children}
    </AuthGuard>
  );
}

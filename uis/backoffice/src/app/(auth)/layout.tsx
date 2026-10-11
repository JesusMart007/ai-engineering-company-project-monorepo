import { GuestOnly } from "@/components/GuestOnly";

export default function AuthLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <header className="topbar">
        <span className="brand">Nexova · Backoffice</span>
      </header>
      <GuestOnly>{children}</GuestOnly>
    </>
  );
}

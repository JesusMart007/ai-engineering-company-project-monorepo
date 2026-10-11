// Pages anyone can open, signed in or not (e.g. the link in a reset email): no guard, no redirect.
export default function PublicLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <header className="topbar">
        <span className="brand">Nexova · Backoffice</span>
      </header>
      {children}
    </>
  );
}

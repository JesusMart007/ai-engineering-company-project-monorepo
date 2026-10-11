import ErrorState from '../components/ErrorState';

export default function NotFound() {
  return (
    <main className="max-w-3xl mx-auto w-full px-4 py-10">
      <ErrorState title="Página no encontrada" message="La dirección que has abierto no existe o ha cambiado." />
    </main>
  );
}

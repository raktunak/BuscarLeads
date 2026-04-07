import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VenderWEB - Lead Generation",
  description: "Genera listas de clientes potenciales por vertical y region",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}

import "./globals.css";

export const metadata = {
  title: "Jarvis Assistant",
  description: "Jarvis Assistant Phase 1"
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

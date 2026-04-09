import "./globals.css";

export const metadata = {
  title: "Jarvis Operator Console",
  description: "Guided solo-operator interface for approvals, tasks, and safe automation"
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

import { Badge as UIBadge } from "@/components/ui/badge";

const variants = {
  success: "default",
  warning: "secondary",
  danger: "destructive",
  neutral: "outline",
};

export default function Badge({ children, variant = "neutral", className = "" }) {
  const v = variants[variant] || "outline";
  return (
    <UIBadge variant={v} className={className}>
      {children}
    </UIBadge>
  );
}

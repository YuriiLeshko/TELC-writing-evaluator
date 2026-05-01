import {
  Card as UICard,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Card({ title, children, className = "", muted = false, style }) {
  const cls = [muted ? "bg-muted" : "", className].filter(Boolean).join(" ");
  return (
    <UICard className={cls} style={style}>
      {title ? (
        <CardHeader className="p-4 pb-2">
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      ) : null}
      <CardContent className="p-4 pt-0">{children}</CardContent>
    </UICard>
  );
}

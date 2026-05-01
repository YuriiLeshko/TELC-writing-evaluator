import { Button as UIButton } from "@/components/ui/button";

const variants = {
  primary: "default",
  secondary: "secondary",
  danger: "destructive",
  ghost: "ghost",
};

export default function Button({
  children,
  variant = "primary",
  type = "button",
  className = "",
  ...rest
}) {
  const v = variants[variant] || "default";
  return (
    <UIButton type={type} variant={v} className={className} {...rest}>
      {children}
    </UIButton>
  );
}

import { useEffect, useRef } from "react";

export default function Textarea({ className = "", mono = false, value, onChange, ...rest }) {
  const ref = useRef(null);

  const autosize = () => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  };

  useEffect(() => {
    autosize();
  }, [value]);

  const cls = ["textarea", mono ? "textarea--mono" : "", className].filter(Boolean).join(" ");
  return (
    <textarea
      ref={ref}
      className={cls}
      value={value}
      onChange={onChange}
      onInput={autosize}
      {...rest}
    />
  );
}

import "./shimmer.css";

export default function Shimmer({ children, as: Tag = "span", duration = 2, spread = 2, className = "" }) {
  return (
    <Tag
      className={"shimmer " + className}
      style={{
        "--shimmer-duration": duration + "s",
        "--shimmer-spread": spread,
      }}
    >
      {children}
    </Tag>
  );
}

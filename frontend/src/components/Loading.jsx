function Loading({ text = "Loading data..." }) {
  return (
    <div className="loading-spinner-container">
      <div className="loading-spinner" />
      <span className="text-muted text-sm font-medium">{text}</span>
    </div>
  );
}

export default Loading;

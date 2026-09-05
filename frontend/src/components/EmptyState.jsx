function EmptyState({ title = "No Data Found", message = "There is no information to display at this time." }) {
  return (
    <div className="empty-state-box">
      <div className="empty-state-icon">📂</div>
      <h3 className="card-title mb-2">{title}</h3>
      <p className="text-muted text-sm">{message}</p>
    </div>
  );
}

export default EmptyState;

import styles from "./MetersFilterBar.module.css";

interface MetersFilterBarProps {
  statusOptions: string[];
  severityOptions: string[];
  selectedStatus: string | null;
  selectedSeverity: string | null;
  searchQuery: string;
  onStatusChange: (status: string | null) => void;
  onSeverityChange: (severity: string | null) => void;
  onSearchChange: (query: string) => void;
}

export function MetersFilterBar({
  statusOptions,
  severityOptions,
  selectedStatus,
  selectedSeverity,
  searchQuery,
  onStatusChange,
  onSeverityChange,
  onSearchChange,
}: MetersFilterBarProps) {
  return (
    <div className={styles["meters-filter-bar"]}>
      <div className={styles["meters-filter-bar__filter-group"]}>
        <label htmlFor="search-filter" className={styles["meters-filter-bar__label"]}>
          Buscar:
        </label>
        <input
          id="search-filter"
          type="text"
          className={styles["meters-filter-bar__input"]}
          placeholder="Buscar por ID o nombre..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <div className={styles["meters-filter-bar__filter-group"]}>
        <label htmlFor="status-filter" className={styles["meters-filter-bar__label"]}>
          Estado:
        </label>
        <select
          id="status-filter"
          className={styles["meters-filter-bar__select"]}
          value={selectedStatus || ""}
          onChange={(e) => onStatusChange(e.target.value || null)}
        >
          <option value="">Todos</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      <div className={styles["meters-filter-bar__filter-group"]}>
        <label htmlFor="severity-filter" className={styles["meters-filter-bar__label"]}>
          Severidad:
        </label>
        <select
          id="severity-filter"
          className={styles["meters-filter-bar__select"]}
          value={selectedSeverity || ""}
          onChange={(e) => onSeverityChange(e.target.value || null)}
        >
          <option value="">Todas</option>
          {severityOptions.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

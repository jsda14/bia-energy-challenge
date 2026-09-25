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
    <div className={styles.filterBar}>
      <div className={styles.filterGroup}>
        <label htmlFor="search-filter" className={styles.label}>
          Buscar:
        </label>
        <input
          id="search-filter"
          type="text"
          className={styles.input}
          placeholder="Buscar por ID o nombre..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <div className={styles.filterGroup}>
        <label htmlFor="status-filter" className={styles.label}>
          Estado:
        </label>
        <select
          id="status-filter"
          className={styles.select}
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

      <div className={styles.filterGroup}>
        <label htmlFor="severity-filter" className={styles.label}>
          Severidad:
        </label>
        <select
          id="severity-filter"
          className={styles.select}
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

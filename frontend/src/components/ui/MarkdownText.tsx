import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import styles from "./MarkdownText.module.css";

interface MarkdownTextProps {
  content: string;
}

export function MarkdownText({ content }: MarkdownTextProps) {
  return (
    <div className={styles["markdown-text"]}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: (p) => <p className={styles["markdown-text__paragraph"]} {...p} />,
          ul: (p) => <ul className={styles["markdown-text__list"]} {...p} />,
          ol: (p) => <ol className={styles["markdown-text__list"]} {...p} />,
          li: (p) => <li className={styles["markdown-text__list-item"]} {...p} />,
          table: (p) => (
            <div className={styles["markdown-text__table-wrapper"]}>
              <table className={styles["markdown-text__table"]} {...p} />
            </div>
          ),
          th: (p) => <th className={styles["markdown-text__table-header"]} {...p} />,
          td: (p) => <td className={styles["markdown-text__table-cell"]} {...p} />,
          strong: (p) => <strong className={styles["markdown-text__strong"]} {...p} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

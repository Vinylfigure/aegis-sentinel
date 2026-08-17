import styles from "./StubPage.module.css";

export interface StubPageProps {
  title: string;
  /** Execution-plan task that fills this page in (e.g. "A3", "B2"). */
  plannedIn: string;
  description: string;
}

/** Placeholder body for a planned route. Replaced as its track lands. */
export function StubPage({ title, plannedIn, description }: StubPageProps) {
  return (
    <article className={styles.stub}>
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.badge}>
        <span className={styles.code}>{plannedIn}</span> planned — stub page
      </p>
      <p className={styles.description}>{description}</p>
    </article>
  );
}

import type { User } from "../types";
import GitHubConnectButton from "./GitHubConnectButton";

export default function MemberList({ users }: { users: User[] }) {
  return (
    <div className="member-grid">
      {users.map((user) => (
        <div className="member-card" key={user.id}>
          <span className="member-avatar">{user.name.charAt(0)}</span>
          <a href={`/users/${user.id}`} data-link>
            <strong>{user.name}</strong>
            <small>{user.role}</small>
          </a>
          <GitHubConnectButton userId={user.id} initialUsername={user.githubUsername ?? null} />
          <a
            className="card-arrow"
            href={`/users/${user.id}`}
            data-link
            aria-label={`Open ${user.name} dashboard`}
          >
            →
          </a>
        </div>
      ))}
    </div>
  );
}

export type GroupRole = 'owner' | 'admin' | 'co_leader' | 'deputy' | 'member';

const ROLE_RANKS: Record<string, number> = {
  owner: 4,
  admin: 4,
  co_leader: 3,
  deputy: 2,
  member: 1,
};

const ROLE_LABELS: Record<string, string> = {
  owner: 'Trưởng nhóm',
  admin: 'Trưởng nhóm',
  co_leader: 'Đồng thủ lĩnh',
  deputy: 'Phó nhóm',
  member: 'Thành viên',
};

export function getGroupRoleRank(role?: string | null): number {
  if (!role) return 1;
  return ROLE_RANKS[role] ?? 1;
}

export function getGroupRoleLabel(role?: string | null): string {
  if (!role) return 'Thành viên';
  return ROLE_LABELS[role] ?? 'Thành viên';
}

export function isGroupTopLeader(role?: string | null): boolean {
  return getGroupRoleRank(role) >= 4;
}

export function isGroupLeaderOrCoLeader(role?: string | null): boolean {
  return getGroupRoleRank(role) >= 3;
}

export function isGroupPrivileged(role?: string | null): boolean {
  return getGroupRoleRank(role) >= 2;
}

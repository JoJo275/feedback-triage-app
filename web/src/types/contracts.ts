export type ExtensibleString<T extends string> = T | (string & {});

export type UserRole = ExtensibleString<"admin" | "team_member" | "demo">;
export type WorkspaceRole = ExtensibleString<"owner" | "team_member">;

export type FeedbackStatus = ExtensibleString<
    | "new"
    | "needs_info"
    | "reviewing"
    | "accepted"
    | "planned"
    | "in_progress"
    | "shipped"
    | "closed"
    | "spam"
    | "rejected"
>;

export type FeedbackSource = ExtensibleString<
    | "email"
    | "interview"
    | "reddit"
    | "support"
    | "app_store"
    | "twitter"
    | "web_form"
    | "other"
>;

export interface UserDto {
    id: string;
    email: string;
    is_verified: boolean;
    role: UserRole;
    theme_preference: string;
    created_at: string;
}

export interface MembershipDto {
    workspace_id: string;
    workspace_slug: string;
    workspace_name: string;
    role: WorkspaceRole;
}

export interface WorkspaceDto {
    id: string;
    slug: string;
    name: string;
    is_demo: boolean;
    public_submit_enabled: boolean;
    created_at: string;
}

export interface MeResponse {
    user: UserDto;
    memberships: MembershipDto[];
}

export interface FeedbackItemDto {
    id: number;
    title: string;
    description: string | null;
    source: FeedbackSource;
    pain_level: number;
    status: FeedbackStatus;
    created_at: string;
    updated_at: string;
}

export interface FeedbackListEnvelope {
    items: FeedbackItemDto[];
    total: number;
    skip: number;
    limit: number;
}

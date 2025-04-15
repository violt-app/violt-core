export interface User {
    id?: string;
    name: string;
    email: string;
    username: string;
    password?: string;
    terms_accepted?: boolean;
}
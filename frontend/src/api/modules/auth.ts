import client from '../client'

export const authApi = {
    login: (data: { username: string; password: string }) =>
        client.post('/auth/login/', data),

    logout: () =>
        client.post('/auth/logout/'),

    getUserInfo: () =>
        client.get('/auth/user-info/'),
}

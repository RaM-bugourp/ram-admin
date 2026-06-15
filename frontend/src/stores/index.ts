import { createStore } from 'vuex'
import user from './user'
import ai from './ai'

export default createStore({
    modules: { user, ai },
})

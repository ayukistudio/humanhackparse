interface IAuthStore {
  $id: string
  email: string
  name: string
  status: boolean
}

const defaultValue: {user: IAuthStore} = {
  user: {
    $id: '',
    email: '',
    name: '',
    status: false
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => defaultValue,
  getters: {
    isAuth: state => state.user.status,
    user_id: state => state.user.$id
  },
  actions: {
    clear() {
      this.$patch(defaultValue)
    },
    set(input: IAuthStore) {
      this.$patch({user: input})
    }
  }
})

export const useIsLoadingStore = defineStore('isLoading', {
  state: () => ({
    isLoading: false
  }),
  actions: {
    set(data: boolean) {
      this.$patch({isLoading: data})
    }
  }
})

export const useIsLoadingStoreProd = defineStore('useIsLoadingProd', {
  state: () => ({
    isLoading: false
  }),
  actions: {
    set(data: boolean) {
      this.$patch({isLoading: data})
    }
  }
})


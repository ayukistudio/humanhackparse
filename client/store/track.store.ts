import { defineStore } from 'pinia'
import { COLLECTION_PRODUCTS, DB_ID } from '~/app.constants'
import type { Models } from 'appwrite'
import { DB } from '~/lib/appwrite'

export interface Product extends Models.Document {
	title: string,

}

export const useProductStore = defineStore('product', {
	state: () => ({ 
		products: ref<Product[]>([]),
		loading: ref<boolean>(false),
		error: ref<string | null>(null)
	}),

	actions: {
		async fetchProducts(): Promise<void> {
			this.loading = true
			try {
				const response = await DB.listDocuments<Product>(DB_ID, COLLECTION_PRODUCTS)
                console.log(response)
				this.products = response.documents
			} catch (err: any) {
				this.error = err.message
			} finally {
				this.loading = false
			}
		},
		setProducts(products: Product[]): void {
            console.log(products)
			this.products = products
		}
	}
})

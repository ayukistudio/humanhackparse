<script setup lang="ts">
import {
	Sidebar,
	SidebarContent,
	SidebarGroup,
	SidebarHeader,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
	SidebarMenuSub,
	SidebarMenuSubButton,
	SidebarMenuSubItem,
	type SidebarProps,
	SidebarRail
} from '@/components/ui/sidebar'

import { COLLECTION_PRODUCTS, DB_ID } from '~/app.constants'
import { DB } from '~/lib/appwrite'

import { GalleryVerticalEnd } from 'lucide-vue-next'
import type { Product } from '~/store/track.store'

const props = defineProps<SidebarProps>()
const products = ref()

const productStore = useProductStore()

</script>

<template>
	<Sidebar v-bind="props">
		<SidebarHeader>
			<SidebarMenu>
				<SidebarMenuItem>
					<SidebarMenuButton
						size="lg"
						as-child
					>
						<NuxtLink to="/">
							<div
								class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground"
							>
								<GalleryVerticalEnd class="size-4" />
							</div>
							<div class="flex flex-col gap-0.5 leading-none">
								<span class="font-semibold">Sauce Tracker</span>
								<span class="">v1.0.0</span>
							</div>
						</NuxtLink>
					</SidebarMenuButton>
				</SidebarMenuItem>
			</SidebarMenu>
		</SidebarHeader>
		<SidebarContent>
			<SidebarGroup>
				<SidebarMenu>
					<SidebarMenuItem
						v-if="productStore.products.length > 0"
						v-for="product in productStore.products"
						:key="product.user_id"
					>
						<SidebarMenuButton class="flex flex-col items-start gap-10 overflow-hidden" as-child>
							<NuxtLink :to='`/product/${product.$id}`' class="font-normal">
								{{ product.title }}
							</NuxtLink>
						</SidebarMenuButton>
					</SidebarMenuItem>
					<div
						v-else
						class="text-center"
					>
						Здесь будут сохраненные товары...
					</div>
				</SidebarMenu>
			</SidebarGroup>
		</SidebarContent>
		<SidebarRail />
	</Sidebar>
</template>

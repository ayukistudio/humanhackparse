<template>
	<div class="w-full h-full mt-[9%] flex flex-col gap-5 items-center justify-center">
		<NuxtImg
			src="/loader.svg"
			alt=""
			width="150"
		/>
		<p class="text-center">{{ placeholderRef }}</p>
	</div>
</template>

<script setup>
const placeholderRef = ref('Ищем лучшие товары для вас...')
setTimeout(() => {
	placeholderRef.value = 'Подбираем лучшие предложения...'
}, 5000)
setTimeout(() => {
	placeholderRef.value = 'Пытаемся как можно скорее...'
}, 10000)
setTimeout(() => {
	placeholderRef.value = 'Это займет время, но оно того стоит...'
}, 15000)
setTimeout(() => {
	placeholderRef.value = 'Ожидайте, самые лучшие предложения вы найдете только тут...'
}, 20000)
</script>

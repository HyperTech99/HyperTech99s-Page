<template>
  <div id="app">
    <router-view/>
  </div>
</template>

<script>
export default {
  async beforeMount() {
    try {
      await this.$store.dispatch('getProfile');
      await this.$store.dispatch('getActivity');
      await this.$store.dispatch('getSkillCategory');
      await this.$store.dispatch('getSkillList');
      await this.$store.dispatch('getProjectCategory');
      await this.$store.dispatch('getProjectList');
    } catch (error) {
      alert(error);
    }
  }
}
</script>

<style lang="scss">
body {
  margin: 0;
}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

</style>

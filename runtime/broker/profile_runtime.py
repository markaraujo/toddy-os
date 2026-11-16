"""Captured per-profile runtime routing; no selected-core task retargeting."""
try:
    from .profiles import ProfileError
    from .profile_registry import RegistryError
    from .tasks import TaskError
except ImportError:
    from profiles import ProfileError
    from profile_registry import RegistryError
    from tasks import TaskError


class ProfileRuntime:
    def __init__(self,registry,factory):
        self.registry,self.factory=registry,factory
        self.contexts={}

    def context(self,profile_id):
        if profile_id not in self.contexts:
            profiles=self.registry.store(profile_id,allow_recovery=True)
            context=self.factory(profiles)
            # Factory owns recovery exactly once, after lifetime ownership locks.
            # Backfill accepted legacy task metadata before exposing dispatch.
            with profiles._db() as db:
                task_ids=[row[0] for row in db.execute('SELECT id FROM tasks ORDER BY rowid')]
            for task_id in task_ids:self.registry.bind_task(task_id,profile_id)
            self.contexts[profile_id]=context
        return self.contexts[profile_id]

    def selected(self):
        return self.context(self.registry.active()['profile_id'])

    def task(self,task_id):
        location=self.registry.locate_task(task_id)
        return self.context(location['profile_id'])

    @staticmethod
    def snapshot(context,task_id,*,reconcile=False):
        view=context.core.reconcile(task_id) if reconcile else context.journal.inspect(task_id)
        return {**view,'profile_id':context.profiles.profile_id}

    def capabilities(self):
        selected=self.registry.active()
        try:
            caps=self.selected().core.capabilities()
        except (ProfileError,RegistryError,TaskError):
            caps={'version':1,'profile_schema':1,'store_version':1,
                  'profile_id':selected['profile_id'] or 'toddy-default','profile_revision':'0'*64,
                  'features':['durable-tasks','cancel','profiles','profile-settings-v1'],
                  'agent_backend':False,'provider_mode':'deferred','tools':[],
                  'recovery_required':True}
        caps={**caps,'features':list(caps['features'])+['named-profiles-v1','task-history-v1'],
              'registry_generation':selected['generation']}
        return caps

    def list_profiles(self):
        value=self.registry.list_profiles()
        return {'version':1,'active_profile_id':self.registry.active()['profile_id'],
                'generation':value['generation'],'profiles':[
                    {'id':row['profile_id'],'display_name':row['display_name'],
                     'revision':row['profile_revision'],'health':row['status'],'selected':row['selected']}
                    for row in value['profiles']]}

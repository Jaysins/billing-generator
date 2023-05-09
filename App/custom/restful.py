import falcon

from App.custom.errors import Unauthorized


def public_query(query, **kwargs):
    """

    @param query:
    @type query:
    @param kwargs:
    @type kwargs:
    @return:
    @rtype:
    """
    return query


def double_query(query, **kwargs):
    """

    @param query:
    @type query:
    @param kwargs:
    @type kwargs:
    @return:
    @rtype:
    """
    user_context = kwargs.get("user_context", {})
    print("theconcccccccc", user_context)
    raw_query = {"instance_id": user_context.get("instance_id")}
    entity_id = kwargs.get("entity_id", None)
    if entity_id:
        raw_query.update(entity_id=entity_id)
    else:
        raw_query.update(user_id=user_context.get("user_id"))
    return query.raw(raw_query)


def double_permit(obj, user_context, req, entity_context=None, id_context=None, **kwargs):
    """

    """
    if not obj:
        return
    resource_name = req.context.get("resource_name", None)
    if not resource_name:
        return obj
    context_instance_id = user_context.get("instance_id")
    context_user_id = user_context.get("user_id")
    context_entity_id = req.context.get("entity_id")
    target_id = context_entity_id if context_entity_id else context_user_id
    if not target_id:
        raise falcon.HTTPError('401 ', title='Unauthorized', description="You are not permitted to view this object",
                               code=1839)
    user_id = getattr(obj, "user_id", None)
    instance_id = getattr(obj, "instance_id", None)
    entity_id = getattr(obj, "entity_id", None)
    if instance_id == context_instance_id and (user_id == target_id or entity_id == target_id):
        return obj
    raise falcon.HTTPError('401 ', title='Unauthorized', description="You are not permitted to view this object",
                           code=1839)


def public_permit(obj, user_context, req, **kwargs):
    """

    @param obj:
    @type obj:
    @param user_context:
    @type user_context:
    @param req:
    @type req:
    @param kwargs:
    @type kwargs:
    @return:
    @rtype:
    """
    return obj


def entity_query(query, **kwargs):
    """

    """
    return query.raw({"entity_id": kwargs.get("req").context.get("entity_id"),
                      "instance_id": kwargs.get("user_context", {}).get("instance_id")})


def entity_permit(obj, user_context, req, entity_context=None, id_context=None, **kwargs):
    """

    @param obj:
    @param user_context:
    @param req:
    @param entity_context:
    @param id_context:
    @param kwargs:
    @return:
    """
    mod_entity_id = getattr(obj, "entity_id", None)
    mod_instance_id = getattr(obj, "instance_id", None)
    if mod_entity_id == req.context.get("entity_id") and mod_instance_id and user_context.get("instance_id"):
        return obj
    raise falcon.HTTPError('401 ', title='Unauthorized', description="You are not permitted to view this object",
                           code=1839)



def admin_query(query, **kwargs):
    """

    @param query:
    @type query:
    @param kwargs:
    @type kwargs:
    @return:
    @rtype:
    """
    print("query wkww==>")
    print(kwargs)

    profile = kwargs.get("user_context").get("profile")

    if profile.get("role") not in ["default", "franchise"]:
        raise Unauthorized({'invalid_credentials': "You are not permitted to view this object"}, code=1839)

    print(kwargs.get("req").context)
    return query


def admin_permit(obj, user_context, req, **kwargs):
    """

    @param obj:
    @type obj:
    @param user_context:
    @type user_context:
    @param req:
    @type req:
    @param kwargs:
    @type kwargs:
    @return:
    @rtype:
    """

    print("in this mofff")
    profile = user_context.get("profile")

    if profile.get("role") not in ["default", "franchise"]:
        raise Unauthorized({'invalid_credentials': "You are not permitted to view this object"}, code=1839)

    print(user_context)
    print(req)
    print(kwargs)
    return obj


def instance_permit(obj, user_context, req, entity_context=None, id_context=None, **kwargs):
    """

    @param obj:
    @param user_context:
    @param req:
    @param entity_context:
    @param id_context:
    @param kwargs:
    @return:
    """
    if getattr(obj, "instance_id", None) and user_context.get("instance_id"):
        return obj
    raise falcon.HTTPError('401 ', title='Unauthorized', description="You are not permitted to view this object",
                           code=1839)


def instance_query(query, **kwargs):
    req = kwargs.get("req")
    id_context = req.context.get("id_context")
    instance_id = id_context.instance_id if id_context else None
    raw_query = {"instance_id": instance_id}
    return query.raw(raw_query)

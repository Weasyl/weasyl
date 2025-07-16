const loginName = username =>
    username.replace(/[^a-z0-9]/gi, '');

export default loginName;

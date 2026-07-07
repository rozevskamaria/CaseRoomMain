import { graphql } from "../gql";

export const MeQuery = graphql(`
  query Me {
    me {
      id
      role
      status
      loginName
      email
      fullName
    }
  }
`);

export const RequestLoginLinkMutation = graphql(`
  mutation RequestLoginLink($loginName: String!) {
    requestLoginLink(loginName: $loginName) {
      ok
    }
  }
`);

export const RegisterStudentMutation = graphql(`
  mutation RegisterStudent($loginName: String!, $fullName: String) {
    registerStudent(loginName: $loginName, fullName: $fullName) {
      ok
    }
  }
`);

export const ConsumeMagicLinkMutation = graphql(`
  mutation ConsumeMagicLink($token: String!) {
    consumeMagicLink(token: $token) {
      ok
      reason
    }
  }
`);

export const LogoutMutation = graphql(`
  mutation Logout {
    logout {
      ok
    }
  }
`);

export const DevLoginMutation = graphql(`
  mutation DevLogin($loginName: String!) {
    devLogin(loginName: $loginName) {
      ok
      reason
    }
  }
`);

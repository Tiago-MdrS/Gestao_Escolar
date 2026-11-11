export interface PerfilResumo {
  nome: string;
}

export interface UsuarioAutenticado {
  id: number;
  nome_completo: string;
  email: string;
  perfil: PerfilResumo;
  permissoes: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}